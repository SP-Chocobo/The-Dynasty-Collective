# #222 / #216 — where this stands

Last updated 2026-09-10. **No engine source has been changed in this entire investigation.**
`draft_room.py`, `lineup_optimizer.py` and `pick_synthesis.py` are byte-identical to where it
started. Everything below is measurement, evidence, doctrine, and prose.

**`BRIEF_NEXT_SESSION.md` is COMPLETE (`f67ec5b`) — do not re-run it; read
`STEP1_WHAT_UPSIDE_MODE_IS_FOR.md` and `STEP2-4_THE_ANSWER.md` for what it found.
The open work is now the RESIDUAL and B2, at the bottom of this file.**

**The original brief: `BRIEF_NEXT_SESSION.md`. Read it after this
file and follow it — it defines the one question that is in scope and the four things
that are explicitly not.**

Read this before touching anything. Six suspects have been cleared here, four of them after a
published finding of mine had to be withdrawn.

---

## The observation that started it

A complete 12×26 startup on Fourth and Forever's real rulebook — production engine on every
chair, real Sleeper universe (6,595), real season projections (5,346) scored under this
league's own settings — against that league's twelve real managers.

| | QB | RB | WR | **TE** |
|---|---|---|---|---|
| twelve real managers | 20.0% | 27.4% | 37.1% | **15.5%** |
| the engine | **10.3%** | 26.9% | 30.4% | **32.4%** |

## THE SCOREBOARD

| component | verdict |
|---|---|
| `replacement_levels` | ✅ correct — level lands at the demand rank on a real named player |
| `displacement_level` / the optimizer | ✅ correct — `displaced` constant at 200.90, basis "measured", 7/7 rungs |
| the pre-draft anchor + its provenance | ✅ correct and load-bearing — without the fill, a late board prices NOTHING |
| `narrow_candidates` / `_board_order` / `feasibility_first` | ✅ exonerated — additive, overrode nothing, backstop never bound |
| the measurement framework | ✅ can now distinguish valuation trajectories (`upside_from_round`, `picks_by_mode`) |
| flex-share candidate | ❌ FROZEN — do not revive |
| D3 live-alternative fix | ❌ KILLED by its own gate |
| **mode transition (round 15)** | **⚠ ANSWERED as a design gap (`f67ec5b`) — the concept is missing for lack of a DECISION, not material. Escalated: what is upside mode FOR?** |
| **residual TE + B2 (backup QB)** | **⚠ OPEN, unattributed, no suspect** |

## What is actually established

**1. The B1 ladder is explained, and it is not a defect.** `displacement_adj` returning to
−51.73 at 7 and 8 tight ends held is the LEVEL returning to 149.17 by changing basis (live →
pre-draft anchor). One constant reached twice. The optimizer never moves.

**2. The level CANCELS.** `bpa = points − L` and `displacement_adj = L − displaced`, same L, and
`_scale_vor_to_bpa` is the identity — so `bpa + adj = points − displaced` and the basis is
irrelevant wherever the term is non-zero. Measured monotonic across the ladder. This is why D3
died: a "live" `free_alternative` with `bpa` unchanged would have injected the anchor's
staleness as an ~86-point penalty per surplus tight end. **A derived-looking fix that would have
made the engine worse.**

**3. The mode boundary is causally active — 63% of the excess, and NOT the whole cause.**
`UPSIDE_MODE_DEFAULT_ROUND = 15`; the upside branch zeroes every team-specific term ("no roster
awareness of any kind", its own comment). Ablation, `mode="balanced"` forced for 26 rounds,
control clean (rounds 1–14 identical 168/168, diverging at exactly pick 169):

| rounds 15–26 | TE |
|---|---|
| AUTO (upside) | 52.1% |
| ABLATION (balanced) | **29.2%** |

**Do not ship "force balanced".** It is measured and rejected: whole-draft WR goes 30.4% → 42.0%
(human 37.1%), largest single-position pile 12 → 19, seats with ≥12 at one position 3 → 7.

**4. The transition is UNDEFINED, not merely mis-set.** Five existing observables, none equal to
15, spanning sixteen rounds: dedicated slots full → round 7; complete legal lineup fieldable →
rounds 10–11; **the constant → 15**; positions leave the replacement domain → ~17–20; league
starter demand reaches zero → round 23. They disagree because they answer different questions.
The concept has no definition in the engine. **Design gap, not a bad number.**

**Do not pick one.** Lineup-completion fires EARLIER than 15 → more upside picks → *more* tight
ends. Demand-exhaustion fires later. The choice of observable decides the direction, so choosing
now is selection on the outcome. The owner defines the concept first — and note the current
switch is GLOBAL while "this seat is safe" would be per-seat, so even the scope is undefined.

## What was WITHDRAWN (read these before reusing any of it)

- **B1 as published** — mechanism wrong, and `PHASE1_B1_WITHDRAWN.md`'s own replacement
  explanation ("the rank walks back up the thinning list") was also wrong; corrected in place.
- **FINDING_01–04** — measured the 764-row vendor reconstruction, not the 6,595 capture.
- **Phase 2's "rank 37 of 198 REMAINING"** — sampled one of three `replacement_levels` calls.
- **"the narrowing selects the tight ends"** — a picks-SHAPE artifact: no `round` key meant
  `mode="auto"` ran balanced while production ran upside.
- **"the zero QBs are the same fact as the TE shape"** — killed by the ablation. QB is 0.0% in
  rounds 15–26 in BOTH arms. **B2 is independent and remains unexplained.**

## Doctrine earned here (all now in `.claude/skills/engine-measurement/`)

1. Observe the PRODUCTION quantity; never reconstruct it from downstream artifacts.
2. When a function is called more than once per operation, the instrument must say WHICH call —
   tagged from the ARGUMENTS, never call order.
3. Build production's inputs in production's SHAPE. **Behavioural inputs need SCHEMA validation,
   not value validation**: if an omitted field can change derived behaviour, the fixture must
   supply the production schema or fail explicitly.
4. Board rank is not pick order — three ordinals, three names.
5. Save the raw result before deriving anything from it.

## The next two questions, both open, neither owed a fix yet

- **What state should govern the mode transition?** A definition, not an observable.
- **What accounts for the residual?** 29.2% TE survived the ablation, against a human 15.5%.
  Do not let the mode effect become the gravitational centre that explains everything merely
  because it explains a lot — the ablation already showed it does not.

---

# UPDATE — the symmetry break redistributes, it does not create (RESIDUAL5)

Two results, both from artifacts already on disk, no engine run. Basis: ARTIFACT-READ.
The #218 reproduction gate is untouched.

**1. Composition is conserved under pick-order permutation.** base vs 3RR: the SET of 312
drafted players is identical, positional totals identical (QB 32, RB 84, TE 101, WR 95), yet
only 32 of 312 land on the same seat and only 7 of 101 tight ends do. base vs revseat: the
same player at 312 of 312 overalls — the seat LABEL is inert, so every hypothesis reading
`roster_id` is dead; it is slot 9, not roster 9. Only the mode ablation moves composition
(TE 101 → 68, WR 95 → 131, first divergence at overall 171).

**Consequence for the scoreboard:** the hoarder/starver bifurcation has ZERO aggregate
authority. All four team-specific terms together decide who receives a player, never whether
the league takes him. The 32.4%-vs-15.5% gap therefore cannot be explained by finding the
symmetry-breaking variable — permuting it leaves the number at 32.4%. The bifurcation is
demoted from *the culprit* to a second, smaller roster-quality defect. The culprit for the
total sits upstream, where FINDING_01 and PHASE4 already pointed.

**2. Neighbours anti-correlate in the arm that bifurcates.** Statistic and direction specified
by the Fable advisory before it was computed. Lag-1 on the snake lattice, seat-label
permutation null, 200k draws: balanced r = −0.487 (P = 0.0495); base +0.110 (0.762); 3rr
+0.178 (0.840). Independent flips and a fixed per-seat trait both predict ~0; only between-seat
pool contention predicts negative. Marginal at n = 12 in one draft — suggestive, not
established — but it converges with (1), which contention independently predicts.

**18th withdrawal:** RESIDUAL3's "the open-slot mechanism fires 0 times in 144 observations"
is a detector artifact. `adjustment == 0.0` needs `displaced == the TE level`; under
`slot_alternatives` the flex phantom is `max(levels)` = 217.75, above every TE level observed,
so the predicate was arithmetically unreachable. 0 of 144 measured the detector. Doctrine
clause added to the skill.

**Registered and NOT run:** the butterfly test — force one hoarder's +0.01 near-tie the other
way, re-run untouched, read three counts. Contention predicts the perturbed seat moves by
several AND both neighbours move opposite. Signs on record before any reading. ~1,016s, not
authorized.

---

# UPDATE — the aggregate is set by one subtraction, before any pick

Pre-registered in `PREREG_aggregate_selection.md`; result in `RESULT_aggregate_selection.md`.
One opening board, no draft, no engine change.

**The upstream evidence audit the owner asked for.** FINDING_01: **retracted** (vendor
universe), unusable. FINDING_02/03/04: numbers withdrawn, mechanisms unverified. FINDING_05:
engine-vs-human comparison valid and standing; its own pool row quotes the withdrawn vendor
board (corrected in place — 1.36x, not 1.74x) and its stated MECHANISM is superseded.
PHASE4: valid, but identifies a scope mechanism, not an aggregate-selection one.
**Verdict: the existing evidence did NOT resolve the aggregate-selection mechanism.**

**What resolves it.** Ranking the opening priced board (481 rows) and cutting at 312:

| ranked by | QB | RB | WR | **TE** | overlap w/ drafted |
|---|---|---|---|---|---|
| raw projected_points | 35 | 79 | 131 | **67** | 273/312 |
| **bpa = points − level** | 34 | 83 | 94 | **101** | **310/312** |
| full final_score | 34 | 84 | 96 | 98 | 309/312 |
| ACTUALLY DRAFTED | 32 | 84 | 95 | **101** | — |

**The 312-pick draft reproduces a single pre-draft board sort to within three players, and the
entire positional movement happens at ONE step: subtracting the replacement level takes TE from
67 to 101.** The six other score terms move TE by −3. Twelve rosters, 26 rounds of state, the
mode boundary and `narrow_candidates` move it by +3.

**The mechanism, in production quantities.** Levels: QB 243.29, RB 170.81, WR 217.75,
**TE 149.17** — a 94-point spread. The 312 cut is one global bpa threshold (≈ −141.7 at every
position), so it admits a completely different raw player per position: **a TE projecting 7.4
clears it; a WR needs 75.9.** The engine takes 101 of 115 priced tight ends (88% of the pool)
against 94 of 198 receivers (47%).

**This is location, not fault.** `points − level` is value over replacement — the intended
design, correctly implemented, one constant per position derived from this league's own demand
and pool. What is established is that cross-position comparability of VOR in the deep-bench
regime determines the aggregate and essentially nothing else does. That is #155's reserved
question, now measured on the real universe. **Whether a 7.4-point TE should outrank a
75.9-point WR for a bench seat is a design question and it is the owner's.**

**Open, stated as open:** the level cancels mid-draft (`bpa + displacement_adj = points −
displaced`) yet the final composition matches the opening bpa ranking, where it does not
cancel. Compatible — `displaced >= level` always, so displacement can only lower a candidate —
but that compatibility is an inference and is NOT measured.

**Butterfly test: still not run, as instructed.** The bifurcation stays parked as a separate
roster-distribution phenomenon; nothing here shows it feeding back into aggregate selection —
in fact the opposite.
