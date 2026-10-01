# `#52` findings ledger — triage, provenance, and interweaving

> **NOTHING IS FIXED FROM THIS LEDGER UNTIL THE WAVES STOP.** Two reasons. The frozen artifact
> must stay frozen or later waves are not attacking the same target, and the owner's instruction
> stands: build the whole list first, because several of these are larger-scoped or interwoven
> than they look one at a time.
>
> Verdicts are mine, not the passes'. A finding in `wave1/PASS_*.md` is a CLAIM; this file says
> what survived checking.

## Verdict vocabulary

| verdict | meaning |
|---|---|
| **REPRODUCED** | I re-ran it myself and got the reported result |
| **CONFIRMED** | I verified the structural claim directly (read the code / grepped the caller) |
| **CORROBORATED** | both passes found it independently with separate measurements; I have not re-run it |
| **UNVERIFIED** | single pass, plausible, not yet checked |

Novelty is **NEW** or **KNOWN-#nnn**. A KNOWN finding is not worthless — an independent blind
pass reaching a registered item is corroboration that it is real and still live.

## Wave 1 — the ledger

| id | finding | verdict | novelty | class |
|---|---|---|---|---|
| **W1-01** | `displacement_adj` goes **POSITIVE** (+79.44, Travis Hunter) on an IDP league, against a contract that calls it non-positive *by construction*; the pinning test uses `superflex=False` with no IDP slot | **REPRODUCED** | **NEW** | correctness + vacuous pin |
| **W1-02** | `time_horizon_adj` differences percentiles taken over two **different populations**; 225–256 priced rows carry no `proj_3yr` | **CORROBORATED** (A and B, separate numbers) | **NEW** | correctness |
| **W1-03** | Anchor / roster-points cache fingerprint omits `injury_status`, `status`, `years_exp`, names and aliases; stale levels served | **CONFIRMED** (fingerprint block has none of them) | **NEW** | correctness |
| **W1-04** | `test_need_bonus_cannot_flip_a_large_universal_value_gap` is a **tautology** — asserts `top−bottom > MAX` then `top−(bottom+MAX) > 0`, never reads a row's `need_bonus` or `final_score` | **CONFIRMED** (read it) | **NEW** | vacuous test |
| **W1-05** | `prose_names` history shield exempts ~40% of prose blocks carrying a backticked name (`was` alone ~30%); 15–19 dead names hidden; `numeric_constants()` misses derived constants it claims to read | **CORROBORATED** (A 43%/15, B 39.5%/19) | **NEW** | instrument |
| **W1-06** | `test_missing_proj_3yr_is_neutral_not_a_penalty`, cited at `draft_room.py:3137` as proof of W1-02's premise, **does not exist** | **CONFIRMED** (only the citation exists) | **NEW** | false claim |
| **W1-07** | `survival_is_presentable` gates nothing in `app.py` (**0 occurrences**); `pick_necessity` carries a 20% survival weight and is displayed | **CONFIRMED** (grep) | **NEW** | contract breach |
| **W1-08** | `league_config`'s `admits_decision` / `confirmation_state` blocking contract has **no production caller**; and as written would mark the certified fixture league AMBIGUOUS | **CONFIRMED** (no caller) | **NEW** | dead contract |
| **W1-09** | `quantity_readers` classifies `displacement_adj`, `time_horizon_adj`, `risk_adj` as OBSERVABLE though each is an addend of `universal_value` | **UNVERIFIED** | **NEW** | instrument |
| **W1-10** | Two incompatible take models feed one necessity score; `expected_taken` sums to 23.32 over 22 picks | **UNVERIFIED** | KNOWN-`#244`/`#245` family | correctness |
| **W1-11** | Adjustment constants sized for a 0–100 scale now applied to raw points; the prose still describes the old unit | **CORROBORATED** | KNOWN-`#75` | stale prose + sizing |
| **W1-12** | `sleeper_points = scored if scored != 0 else None` collapses a measured zero into "unmeasured", then labels it a coverage gap | **CORROBORATED** | KNOWN-`#187` family | absence contract |
| **W1-13** | `feasibility_first` uses `len(roster_positions)` (includes IR) where `draft_rounds` is absent; mock path reachable | **UNVERIFIED** | **NEW** | correctness |
| **W1-14** | `starter_slot_counts` docstring says the measured flex share is "always supplied"; the seam returns `None`; `slot_share_basis` reaches no production surface | **UNVERIFIED** | KNOWN-`#178` adjacent | false claim |
| **W1-15** | Day-resolution freshness subtraction still shipped where the docstring calls it a fixed defect | **UNVERIFIED** | **NEW** | stale claim |
| **W1-16** | Two homes for the undrafted-slot vocabulary (`HORIZON_UNDRAFTED_SLOTS` vs `league_config.UNDRAFTED_SLOTS`) | **UNVERIFIED** | **NEW** (`#126` class) | duplication |
| **W1-17** | Banker's rounding in `_remaining_demand_rank`; half-share flex leagues land on round-half-even, not a derived rule | **UNVERIFIED** | KNOWN-`#86` | knife-edge |
| **W1-18** | `replacement_levels` end-of-list clamp contradicts `horizon_replacement`'s refusal of the same case | **UNVERIFIED** | KNOWN-`#155` adjacent | inconsistency |
| **W1-19** | `test_one_pricing_universe` asserts a literal source string; correct `**pricing` forwarding would fail it, a comment passes it | **UNVERIFIED** | **NEW** (`#200` class) | instrument |
| **W1-20** | Multi-eligible bucket inconsistency: priced at the vendor position, counted for demand at the first listed | **UNVERIFIED** | KNOWN-`#172` family | inconsistency |

## The interweaving — why these must not be fixed one at a time

Three clusters, and the first is the one that changes how the rest should be read.

### Cluster 1: THIS PROJECT'S OWN REPAIRS CREATED THE TWO WORST FINDINGS

- **`#172` recovered Travis Hunter** from the identity partition — correct, and it is what makes
  **W1-01** reachable. A multi-eligible player was the precondition for the positive
  `displacement_adj`; before that repair the population was empty.
- **`#180`/`#192` routed offence through the scoring-aware path** — correct, and it is what makes
  **W1-02** real. The comment at `draft_room.py:3135` asserting no priced row lacks `proj_3yr`
  was TRUE when written; the repair priced players the vendor never covered and silently falsified
  it.

Neither repair was wrong. Both widened a population that an older invariant had quietly assumed
away. **The lesson is not "be careful" — it is that this repository has no mechanism that
re-checks a stated invariant when the population it ranges over changes.** That is a structural
gap, and fixing W1-01 and W1-02 individually leaves it open.

### Cluster 2: THE INSTRUMENTS THAT SHOULD HAVE CAUGHT CLUSTER 1 WERE THEMSELVES BLIND

**W1-05** (prose shield hides ~40%), **W1-06** (a comment cites a test that does not exist),
**W1-04** (the invariant test is a tautology), **W1-09** (load-bearing terms classified as
observable), **W1-19** (a text-scan where an AST scan exists next door).

W1-06 is the join: the dead test name would have been caught by `prose_names`, except the history
shield exempted the block. **The instrument that would have flagged the stale claim was hiding
it.** And `#283`/`#286` extended that instrument during this session and reported the sweep clean
— a result that was a property of the filter, not of the prose.

Fixing the shield first would likely surface more of Cluster 1 for free. **That is an argument
for ordering, which is exactly what a one-at-a-time repair pass would miss.**

### Cluster 3: SURVIVAL IS WITHHELD AT THE HEADLINE AND LEAKS THROUGH THE DERIVATIVES

**W1-07** (necessity carries 20% survival and is displayed; the "derived fields" list omits it)
and **W1-10** (two take models, one of which manufactures the zeros `#187` forbids). `#206` chose
an enforced refusal; the refusal covers the number and not its consequences.

## Wave 2 — NOT clean, and not close

Eight new findings, plus convergence on Wave 1's core at a rate that settles those beyond doubt.

| id | finding | verdict | novelty |
|---|---|---|---|
| **W2-01** | Contested-identity guard is a function of the REMAINING pool — drafting one twin hands the survivor the vendor record (`trade_value 99.0`, `proj_3yr 840.0`, `identity_basis "matched"`); the roster side never applies the rule at all | CORROBORATED (measured) | **NEW** |
| **W2-02** | `qb_startable_floor` is in VENDOR units, compared against league-scored points. Holds on the fixture by coincidence; on a 4-pt-pass-TD rulebook, QBs in the overall top-24 go **11 → 0** | CORROBORATED (measured) | **NEW** |
| **W2-03** | Superflex: once the startable QB tier is drafted, all 116 remaining QBs are unpriced, sorted below every priced row, and **10 carry `absence_kind=None`** against a stated invariant | CORROBORATED (measured) | **NEW** |
| **W2-04** | `block_opportunity` is **unreachable in production** — 0 fires across 10 board states / 460 candidates; docstring claims ~28% | CORROBORATED (measured) | **NEW** |
| **W2-05** | `trade_value` branch omits `truncated_out=`, clamps to the bottom of a 2-row list, stamps `live_starter_demand`. **Binds on the owner's own league**, on the branch the `#155` fix never reached | CORROBORATED (measured) | **NEW** |
| **W2-06** | QB floor + shared-slot alternative compose into −17.99 on every second QB; **DL −32.87 / DB −28.28 on an EMPTY roster**; 246 of 796 priced rows have TAV < UV against "structurally impossible" | CORROBORATED (measured) | **NEW** |
| **W2-07** | **Thirteen test modules, including `test_cdme_certification`, run on the fixture the repo declares non-production** — its own docstring says "never a synthetic fixture" | CORROBORATED | **NEW** |
| **W2-08** | `CDME_CONTRACTS.md` §1–§3, banner-marked the live authority, false in four places (domain −9.12..97.90 vs measured −319..+220; "never None" vs None on 60% of rows) | CORROBORATED | **NEW** |
| **W2-09** | `round` is the round of the last pick MADE, not the pick being decided; the test pins the off-by-one | UNVERIFIED | **NEW** |
| W2-10 | `remaining_starter_demand` treats `roster_id=None` as a phantom 13th team and raises on the whole board | UNVERIFIED | **NEW** |

### Convergence across all four passes

| finding | A | B | C | D |
|---|---|---|---|---|
| `time_horizon_adj` population mismatch (W1-02) | ✓ | ✓ | ✓ | ✓ |
| survival leaks through `pick_necessity` (W1-07) | ✓ | ✓ | ✓ | ✓ |
| anchor cache key incomplete (W1-03) | ✓ | ✓ | ✓ | — |
| two take models (W1-10) | ✓ | — | ✓ | ✓ |
| `prose_names` shield (W1-05) | ✓ | ✓ | ✓ | — |
| `need_bonus` test is a tautology (W1-04) | — | ✓ | — | ✓ (mutant survived) |

**Four independent passes, four hits on the same two defects.** Those are not opinions any more.

### What Wave 2 changes about the diagnosis

**Cluster 2 grew teeth.** W2-07 is the explanation the first wave was missing: thirteen modules
including the *certification battery* run on a universe with no IDP rows, no unpriced rows, and
`proj_3yr` on every priced row. That is precisely the universe in which W1-02, W2-06 and D-2
**cannot be observed**. The suite is not failing to catch these; it is structurally incapable of
seeing them.

**A new cluster: invariants pinned on the shape where they cannot fail.** W1-01
(`superflex=False`, no IDP slot), W2-06 (`test_an_empty_roster...` on a roster with a dedicated
TE slot and no `slot_alternatives`), W1-04 (algebraically trivial), W2-09 (the test asserts the
off-by-one). Four separate invariants, four pins that cannot fail. That is a *pattern*, not four
accidents, and it is the strongest argument in this ledger against repairing findings one at a
time.

## Wave 3 — NOT clean, and it found the biggest one

| id | finding | verdict | novelty |
|---|---|---|---|
| **W3-01** | **The engine drafts 4–5 KICKERS per roster on the owner's own league.** Found independently by both passes on full multi-round drafts. Every roster legal, so no structural audit fires | **REPRODUCED** (structural cause verified by this session) | **NEW — most serious in the audit** |
| **W3-02** | Live level → pre-draft anchor is a **discontinuity**: WR drifts 225.49 → 214.06, then snaps back to 225.49 when demand hits 0; top bpa moves 0.00 → −11.43 in one pick | CORROBORATED | **NEW** |
| **W3-03** | `remaining_starter_demand` **does not reach zero** when every slot is filled — 25.2 phantom slots remain, and which positions flip to the anchor depends on the flex fill mix | CORROBORATED | **NEW** |
| **W3-04** | `waiting_cost` is `None` for **all 148 QB rows** in superflex — the scarcest position has no waiting cost | CORROBORATED | **NEW** |
| **W3-05** | `waiting_cost` for K swings 7.27 → 116.75 across adjacent picks, on the position the docstring says it estimates best | CORROBORATED | **NEW** |
| **W3-06** | Vendor projection `0.0` admitted as measured while Sleeper `0` becomes `None` — same fact, two contracts | CORROBORATED | **NEW** |
| **W3-07** | SF pace prior yields `survival 0.000` for Josh Allen → **+20 necessity** from a number measured as losing to a constant predictor | CORROBORATED | **NEW** |
| **W3-08** | `test_cdme_certification.test_tav_never_falls_below_universal_value` says "structurally impossible"; **216 priced rows violate it** on the owner's league | CORROBORATED | **NEW** |

### W3-01 is the finding that reframes the freeze

Verified independently by this session, not taken on the passes' word:

```
battery arms: 34 | arms with a K slot: 0 | arms with SUPER_FLEX *and* IDP: 0
owner league:  K True | SUPER_FLEX True | IDP_FLEX 2 | BN 14
```

`#284` — *34 arms, 5,652 picks, **0 structural findings*** — is the result that licensed the
freeze. **It never drafted the owner's roster shape on any of three axes.** `run_roster_proof.py`
and `run_smoke_seats.py` use `build_mock_league` too, which has no K. So `#285`'s quality pass and
`#289`'s freeze condition were measured on shapes the owner does not play either.

The Gate 1 result is not *wrong* — it is true of what it tested. **Its scope is narrower than
every document in this repository implies**, and `FREEZE_RECORD.md` §2 needs that qualification
before it is quoted again.

This also explains a Wave 1 puzzle. Cluster 1 said this repository has no mechanism that
re-checks an invariant when the population changes. W3-01 is the same disease one level up:
**no mechanism checks that the test matrix covers the league the owner actually plays.**

## Wave 4 — NOT clean, by a distance: 29 new, and the audit turned on itself

> **Both passes have now reported.** Pass H took three launches — the first carried the Wave 1
> mandate with no SETUP block and audited a 508-commit-divergent tree before being killed, the
> second died on an account rate limit mid-run. Nothing from either enters this ledger
> (`MANDATE.md` §4). **29 new findings across the two passes**, the most of any wave.

Verdicts below are mine. `wave4/MY_VERIFICATION.md` is what I re-measured, including one
correction to pass G.

| id | finding | verdict | novelty |
|---|---|---|---|
| **W4-01** | **The mechanism of W3-01.** `NEED_BONUS_PER_DEDICATED_SLOT = 4.0` is flat in points and therefore *not* flat in what it buys: 4.00 against the best kicker's 12.57 VOR is **32% of the whole K-to-replacement distance**, and 1.9% of the same distance for Bijan Robinson. Sixteen times steeper for a kicker | **REPRODUCED** (Dicker `bpa 12.57 + need 4.00 = 16.57`, pass G's exact triple) | **NEW** — W3-01 was the symptom, this is the cause |
| **W4-02** | **Two engine constants are derived from a bound the engine violates by 2.4×.** `NECESSITY_DENIAL_SATURATION` (36) and `CONTEXT_ELEVATED_THRESHOLD` (12) derive from `TEAM_SPECIFIC_CAPS`, whose comment excludes `#216`'s fourth term **"deliberately … it is non-positive by construction … so it cannot raise the sum these caps bound"** — the premise measured at +79.44, TAV − UV at 87.82. The tuple exists *precisely* so a fourth term moves the bound automatically; it was hand-exempted on the false premise | **CONFIRMED** (read the derivation chain) | **NEW** — W1-01 is the sign; this is what was built on it |
| **W4-03** | `_picks_by_mode` **asserts what its docstring says it reports** — "actually produced … Reported rather than assumed" computes `(UPSIDE_MODE_DEFAULT_ROUND − 1) × num_teams` and never reads a pick, then is stamped into every trajectory config. Wrong by exactly the round off-by-one it therefore cannot see (168/132 asserted, 169/131 actual) | **CONFIRMED** | **NEW** |
| **W4-04** | **The LLM prompt boundary invites fabrication of the withheld number.** All three system prompts list `survival_probability` / `opportunity_cost` / `expected_value_of_waiting` among "real, already-computed numbers", with the worked example `"19% survival with a QB run detected"`; the evidence block tells the same model it is WITHHELD and "do not estimate one yourself" | **CONFIRMED** | **NEW** — W1-07 is the leak into a score, this is the leak into a prompt |
| ~~**W4-05**~~ | ~~`SUPER_FLEX_QB_SHARE` 0.85 live while the measurement its comment cites returns 1.00~~ **Struck — this is `#184`, and the code says so.** The comment at `draft_room.py:323-328` already states *"0.85 is NOT thereby vindicated… Both values are wrong in the same place… held for owner ruling (#184)"*, and the register carries it as **KNOWN-OPEN-ACCEPTABLE, documented not fixed**. Pass G read the constant and not the fourteen lines above it | **CONFIRMED as already-registered** | **KNOWN-`#184`** |
| **W4-06** | `upside_score` adds `0.5 × (proj3yr_pct − season_pct)` — a **percentile** difference, up to ±50 — to raw-point `bpa`, **unclamped**, where `time_horizon_adj` reads the same pair and clamps to ±10 | **CONFIRMED** (weights read) | **NEW** — same unit class as W1-02, five times the magnitude |
| **W4-07** | Unpriced rows carry a `displacement_adj` stamped basis `measured`; `#203` repaired this shape for `risk_adj` and not for the fourth term or `need_bonus` | **REPRODUCED** (DB −28.28 ×393, DL −32.87 ×219 on an **empty** roster) / UNVERIFIED (the `bpa = NaN` pairing) | **NEW** |
| **W4-08** | Two health models disagree by pricing path: IR + vendor-priced → `risk_adj −18.0`; IR + Sleeper-priced → `risk_adj 0.0`, basis `rule_floor` (≈ −40.7 on a 173-point player) | UNVERIFIED | **NEW** |
| **W4-09** | **Certification drafts a mode production never runs.** Neither `app.py:5024` (Mock) nor `:5381` (Draft Room) passes `mode`; the battery runs `mode="auto"` → 44% upside picks on the owner's 25-round shape, while the late-round *balanced* rounds production does run are covered by no arm (`12T_ppr_mode_balanced` is 14 rounds) | **CONFIRMED** | **NEW** — W3-01's disease on the mode axis instead of the slot axis |
| **W4-10** | `pick_debate._match_candidate` substring fallback returns the first candidate in snapshot order whose name is contained in the text; "Josh Allen over Jalen Hurts" resolves to whichever sorts first. Docstring: "never a guess" | UNVERIFIED | **NEW** |
| **W4-11** | `filter_candidates_by_view` claims candidates are "already sorted by team_acquisition_value descending"; `_board_order` puts `fills_required_slot` first, so the ALL overview's top slice is not the top-N by value when the backstop binds | UNVERIFIED | **NEW** |
| **W4-12** | `draft_board_ui` interpolates names and tag labels into `innerHTML` with only `<` escaped | UNVERIFIED | **NEW** (boundary) |
| **W4-13** | `pick_debate`'s system prompts describe TAV as three terms; the evidence sum has four | UNVERIFIED | **NEW** |
| **W4-14** | `league_format_hint` (`draft_battery.py:215`): `rec >= 1` → ppr, `rec == 0.5` → half_ppr, **else standard**. Every fractional PPR in (0.5, 1.0) — 0.6, 0.75, 0.9 — is priced as if receptions score **nothing**, though 0.75 sits nearer full PPR than standard. The half-PPR test is exact float equality. Its docstring derives the triple "by the same rules `league_format_summary` uses", and those two do agree — agreement between two copies of one rule is not correctness | **CONFIRMED** (read the branch) | **NEW** |
| **W4-15** | Under the capture hint, 18 players' vendor `projection` and 15 winning rows come from `dynasty_superflex_rankings.csv`, which `_detect_rankings_format` tags "standard", in a PPR league | UNVERIFIED | **NEW** |
| — | Two further text-scan guards (`test_depth_basis_boundary.py:45`, `test_tenant_scope_boundary.py:56`) where an AST walk exists in the same suite | UNVERIFIED | KNOWN-class W1-19 (`#200`), two new instances |

**Upgraded by this wave:** W2-09 (round off-by-one) UNVERIFIED → CONFIRMED with measured
consequences; W1-13 (mock `draft_rounds`) UNVERIFIED → CONFIRMED at both call sites; W1-08 and
W1-14 confirmed a second time.

### Wave 4, pass H — fifteen more, and two of them where pass G reported a NULL

| id | finding | verdict | novelty |
|---|---|---|---|
| **W4-16** | **`diff_snapshots` leaks the whole withheld survival family, to the chairs AND to the person.** `_DIFF_FIELDS` includes all three; `format_snapshot_for_llm` prints the deltas into "WHAT CHANGED", `app.py` passes `previous_snapshot` on both surfaces, and the Draft Room's own diff drawer labels them "Survival probability" / "Opportunity cost" / "Value of waiting". Measured 1.01→1.02: `survival_probability: -0.08, opportunity_cost: +17.22` printed directly beneath a block saying the estimate is WITHHELD | CORROBORATED (measured) | **NEW** — the numbers themselves, not a derivative |
| **W4-17** | **The suite pins the leak.** `test_pick_debate.py:57-62` asserts survival is absent from the candidate block; `:88-90` and `:234-239` assert a survival-only delta **does** reach the chair prompt. Two contradictory contracts in one file, and production implements the second | CORROBORATED | **NEW** |
| **W4-18** | **The instrument cannot see slot coverage at all.** `format_axes_exercised` derives its axes from `league_format_hint`'s keys — `scoring`, `superflex`, `te_premium`. Roster-slot composition is not an axis, so the coverage instrument reports "no constant axis" over a matrix with no kicker in it | CORROBORATED | **NEW** — this is *why* W3-01 was invisible |
| **W4-19** | **W3-01 is narrower than the defect.** 51 LB, 51 DB, 16 DL drafted for **24** IDP_FLEX slots; **round 21 was twelve consecutive DBs**; roster 7 spent 15 of 25 picks on K/IDP. Kickers are the visible instance of "positions with a small displacement deduction float up a drained board" | CORROBORATED (measured) | **NEW** — reframes W3-01/W4-01 |
| **W4-20** | **44% of the draft is valued by `bpa` alone.** `growth_signal > 0` on **0 of 131** upside picks; rounds 15–25 run with every team term zeroed and the growth term inert. Round 15 drafted 6 QBs into rosters already holding 2–4 | CORROBORATED (measured) | **NEW** |
| **W4-21** | `upside_score` returns `growth_signal: 0.0` for rows with **no 3-year source at all** (1,996 of 2,028), indistinguishable from a measured flat trajectory, and `draft_board_ui` renders it as `GROWTH 0.0`. `bpa = row.get("bpa") or 0.0` on the same line is a latent None→0.0 | CORROBORATED | **NEW** — `#187` shape, second site this wave |
| **W4-22** | **The necessity pill mostly tells you what round it is.** Every component is non-negative on a baseline of 50, so **no candidate can read below CLOSE CALL before round 15**; the ×0.3 late cap makes anything above LOW URGENCY unreachable after. Measured: round 17 → **17/17 "DOESN'T MATTER MUCH"**. Two of six labels unreachable early, four unreachable late | CORROBORATED (measured) | **NEW** |
| **W4-23** | `--resume` admits a prior arm on `label` alone while capture provenance is stamped at **report level** from the capture on disk *now* — six arms from one universe reported under another's `captured_at` and census, with `commits_present` never firing the reader's only cue | CORROBORATED | **NEW** |
| **W4-24** | **`store_io` drops every subsequent write after ANY `OSError` on read.** `_parse`'s docstring: `readable` is False "only when the file exists, is NOT empty, and does not parse". The code: bare `except OSError: return default, False`. One transient `EACCES`/`EIO` marks the path and `write()` returns silently for the rest of the process | **CONFIRMED — I read it** | **NEW**, and **pass G returned this area as a NULL** |
| **W4-25** | **`pick_debate` has no untrusted fence and no contract**, while `llm_engine` has 11 `untrusted.` call sites. `debate_pick` concatenates the Strategist's and Skeptic's raw prose into the next chair's prompt. The app's own contract text says model-written prior verdicts are exactly what must be fenced | **CONFIRMED — `grep untrusted\|CONTRACT\|fence pick_debate.py` returns nothing** | **NEW**, and **pass G returned this area as a NULL** |
| **W4-26** | The evidence block is **84 candidates / 90,514 characters / ~22.6k tokens**, sent three times per debate. `test_context_budget_boundary.py` — "stays small enough to never be the problem" — asserts on `DEFAULT_NARROW_COUNT = 5 ≤ 30`. The operative count is 84 | CORROBORATED (measured) | **NEW** — vacuous budget test |
| **W4-27** | The decomposition prints an unrounded addend against a rounded sum — `Universal value: 12.57 = bpa 12.569999999999993 + …` — an arithmetic sentence whose two sides visibly differ, handed to a model told never to recompute | CORROBORATED | **NEW** |
| **W4-28** | `parse_caller_verdict` strips the leading `**` but not the closer, so `**CONFIDENCE:** Lean` parses to `'** Lean'` and `app.py` renders "Confidence: ** Lean" verbatim | CORROBORATED (measured) | **NEW** |
| **W4-29** | `settings.get("num_teams", len(league.get("roster_positions", []) and []))` — the default is always `len([])` = 0 | UNVERIFIED | **NEW** (trivial) |
| **W4-30** | `draft_history._atomic_write` is a second, **lock-free** write implementation beside `store_io._write_unlocked` | UNVERIFIED | **NEW** (`#126` class) |

**Corroborated by both passes independently:** the prompt boundary (W4-04), `_match_candidate`
(W4-10), the round off-by-one (W2-09 — both measured 131 actual against 132 recorded), the dead
`league_config` gate (W1-08), the survival leak through `pick_necessity` (W1-07), the fractional-PPR
branch (W4-14), and the kicker result itself.

**One dispute, left open.** G reported 18 players' vendor `projection` and 15 winning rows coming
from a "standard"-tagged export in a PPR league (W4-15). H measured cross-format mixing and called
it a **null** — 0 rows with `projection_source ≠ proj_3yr_source`, and the 34 offence rows from
non-matching exports all tail players. They measured adjacent things and reached opposite
conclusions about hazard. **W4-15 is DISPUTED** and neither pass settles it.

### THE FINDING ABOUT THE AUDIT ITSELF: a pass's null results are not reliable

Pass G examined `store_io` and the untrusted-fence boundary and reported both as null — "atomic
replace, sidecar lock, refuse-to-overwrite-damaged-store, lock depth counting all hold up" and
"`untrusted.fence`/`_report_for_handoff`/`annotate_if_incomplete`: consistent". Pass H found a real
defect in each, and **I confirmed both by reading the code**: `_parse` catches bare `OSError`
against a docstring that says otherwise, and `pick_debate.py` contains not one reference to
`untrusted`, `CONTRACT` or `fence`.

Two of pass G's five null results were wrong.

**This bears directly on the stopping condition.** A wave is declared clean partly on the strength
of its passes' null results, and we now have direct evidence that a pass can examine an area
carefully, report nothing, and be wrong. "Three consecutive waves with no new finding" therefore
cannot mean "three waves that found nothing" — it can only mean "three waves whose *positive*
claims contained nothing new." A null is a report of where a pass looked, not a warrant that
nothing is there, and this ledger should never again treat one as evidence of absence.

### What Wave 4 changes about the diagnosis

**Cluster 1 has a fourth member, and it is the worst kind.** The ledger's first cluster said this
repository has no mechanism that re-checks an invariant when the population it ranges over
changes. W4-02 is that, one turn further: an invariant was not merely left unchecked, it was
**read, believed, and used to justify excluding a term from a bound** — in a comment whose own
next sentence explains that the bound is derived rather than written as `36.0` so that a fourth
term moves it automatically. The author built the guard and then hand-waived it.

**A fourth cluster: the engine's constants are flat in the wrong units.** W4-01 (a per-slot bonus
flat in points, sixteen-fold in fraction-of-spread), W4-06 (percentiles added to points,
unclamped), W1-11 (`#75`, constants sized for a scale that no longer exists) and W2-02
(`qb_startable_floor` in vendor units against league-scored points) are one defect wearing four
coats. **`#56` forbids a calibrated constant; nothing in this repository forbids an
*uncalibrated* one applied across incommensurable scales,** and that is what these four are.

**Cluster 3 reaches the prompt.** W4-04 puts the survival leak somewhere `survival_is_presentable`
structurally cannot reach: a natural-language instruction to an LLM, with a worked example of
citing the number the next block refuses to supply.

## Stopping condition — status

**Wave 1: NOT clean** (9 new). **Wave 2: NOT clean** (8 new). **Wave 3: NOT clean** (8 new, one
of them the most serious of the audit). **Wave 4: NOT clean** (14 new from one pass, one struck on checking, and
**incomplete** — see the Wave 4 banner; its second pass has not reported).

Three consecutive waves producing **no NEW finding that survives verification** — not three waves
producing no findings, which a pass could satisfy by re-reporting known items. **Current streak: 0**, after four waves.

Waves are still finding new, measured, previously unseen defects, and the *kind* is getting worse
rather than better: Wave 1 found broken invariants, Wave 3 found a test matrix that never drafted
the owner's league, and Wave 4 found two shipped constants **derived from** a broken invariant.
The process is nowhere near convergence, which remains the most useful thing it has established.

### PRE-REGISTERED AMENDMENT to the stopping condition (owner, 2026-09-18)

**Written before any clean wave exists.** That is the whole point of writing it now: an amendment
added after a streak has started looks like a reaction to the streak, and this one must not be
readable that way.

Every wave from 2 onward carries a steering paragraph pushing passes away from saturated areas.
It keeps a wave from spending itself on re-reports, and it costs something: a quiet wave is
evidence about the **unexplored surface**, not about the engine. "The engine is clean" and
"steering pushed the passes somewhere nothing lives" produce an identical streak counter.

**The ruling: keep the steering while the streak runs. When three consecutive waves come back
clean, fire one more wave with the blinders OFF** — the mandate minus the steering paragraph,
passes free to sample the saturated areas again.

Pre-registering both outcomes, so the confirmation wave can actually fail:

- **It finds NEW verified findings** → the streak was an artifact of the mandate, not a property
  of the engine. **The count resets to 0** and waves resume, unsteered from then on.
- **It comes back clean** → the three clean waves meant what they appeared to mean, and the
  blinders-off wave is the evidence that says so.

A confirmation wave with no failing outcome is a ceremony. This one has one.

### One thing the waves have now established about themselves

`MANDATE.md` §3 records that the isolation these passes run under is **instructed, not
structural** — each pass builds its own shield with an `archive --exclude` recipe, and Wave 1's
two passes had no excludes at all. Every pass has self-reported clean and the transcripts support
them. But the independence this ledger's corroboration rests on is six agents' compliance, not a
sandbox, and that belongs next to the convergence tables rather than buried in the mandate.
