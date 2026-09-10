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
