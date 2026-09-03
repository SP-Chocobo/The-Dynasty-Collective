# The Engine Wiring Pass

> **What this is.** One session's record, written to be read cold. It exists because six
> findings arrived in an afternoon and were living only in task descriptions and a chat
> transcript. It is a *session log with evidence*, not a contract — `CDME_CONTRACTS.md` and
> `ENGINEERING_DOCTRINE.md` remain authoritative for anything that disagrees.
>
> **Scope note for a later auditor.** The blind adversarial pass (#52) is code-only by
> standing instruction. This document is for the owner, not an audit input. Reading it before
> auditing would defeat the point of the audit being blind.

---

## The one finding underneath the others

The engine's problem is not missing arithmetic. It is a habit of **computing a number and
then not spending it**, in two distinct flavours, and almost everything below is one of them.

### Flavour 1 — write-only quantities

Values produced (or ingested) and then dropped before any decision reads them.

| quantity | where it dies |
|---|---|
| `waiting_cost` | computed in `draft_room._attach_waiting_cost`, rendered as prose, never enters `final_score` / `pick_necessity` / ordering |
| `marginal_value_full_eligibility`, `marginal_value_primary_position_only` | `eligibility_bonus` solves the lineup and returns both; `draft_room.py:1932` reads only their *difference*. Zero production references to either absolute |
| `bye_week` | parsed at `data_merger.py:804` and `:851`, reaches nothing |
| bench depth (`"BN"`) | arrives from Sleeper inside `roster_positions`; counted nowhere. The only other `"BN"` in the tree is a **mock** draft's hardcoded constant |

Plus eleven source-provided fields with no production reader at all (below).

### Flavour 2 — the starters-full collapse

Every quantity the engine computes about *roster need* goes to zero or `None` the moment the
starting lineup is full. Three separate open tickets turned out to be one root cause.

| quantity | behaviour |
|---|---|
| `marginal_lineup_value` | ratio to own value: **1.000** rounds 1–6, 0.097 by round 10, **0.005** by round 12 |
| `need_bonus` | spread collapses to 0.67 (~2–3% of the value spread) from round 10 |
| `estimated_bench_demand` | returns `None` from round 13 — the **sole** cause of every missing `waiting_cost` |

The engine has no model of bench value, so everything depth-dependent dies exactly when depth
decisions start. Filed separately as #62, #115, and the round-13 `waiting_cost` cliff; they are
one defect.

---

## What was built

### `depth_exposure()` — depth is what a hole costs, not what a slot wants

Removes each starter, re-solves the lineup, and reports what the hole costs. Two properties
fall out of the assignment solve rather than being encoded as rules:

**Self-limiting.** One TE: losing him costs 15. Add a TE2 worth 13 → costs 2. Add a *third*
TE → still 2. The third buys exactly zero insurance. No rule says "you don't need four tight
ends"; the arithmetic does. A *bad* backup (worth 3) leaves 12 exposed, so the number tracks
the quality of the cover, not merely its existence.

**Substitutability.** A spare RB improves RB *and* WR — the FLEX slot is shared. A spare TE
improves only TE, and improves it enormously, because nothing else can start in a mandatory TE
slot. That asymmetry is why TE depth behaves unlike RB depth, and it is discovered, not asserted.

**Four states**, because the numbers are returned in all of them and only one makes them
evidence: `measured` / `no_surplus` / `vacant` / `not_applicable`.

`no_surplus` was found by measurement, not design. The self-limiting property does **not**
hold while every rostered body is on the field — nothing can backfill, so every loss costs full
value and the number is each starter's own value wearing a depth-shaped label. Real arithmetic
carrying no depth information. Marked rather than suppressed, because the reader most likely to
see it is drafting in round 3.

**No invented probability.** "Any one starter could become unavailable" is a uniform stated
assumption. `RISK_ADJ` is a current-status penalty, not a prospective rate, and no per-position
injury base rate exists here. A risk multiplier is a socket left honestly empty; a test fails if
a `POSITION_RISK`-style constant ever appears in the module.

### What this model is NOT, and why that matters next

Depth is insurance against a starter being unavailable. Insurance has two halves — **severity**
(what the hole costs) and **frequency** (how often the hole opens). This pass built severity
only, and the frequency socket is deliberately empty rather than filled with a guess.

That is a real limit, not a formality: two positions with identical exposure are currently
treated identically even if one loses starters twice as often. What would close it does not
exist in this data — `injury_flag` is 16 rows of 2600, and suspension will never be structured.

**`bye_week` is the exception, and it is the only piece of the frequency half this app can
compute.** It is also a different KIND of quantity from the rest: a bye is not a risk. It is
probability 1.0 on a known date. Every player misses exactly one week and the week is published.
So two starters sharing a bye is not exposure to something that might happen — it is a
*scheduled outage*, visible in advance, and the only case where the engine could say "you will
have this hole, in week 9" rather than "you might."

That argues for treating bye overlap as its own term rather than as a multiplier on exposure:
certainty and risk should not be summed into one number, for the same reason `horizon_basis`
distinguishes a measured floor from an imputed one.

### `bench_capacity()`

`roster_positions.count("BN")`. Depth was unbounded in an engine whose real leagues bound it.

---

## What was measured

**`depth_exposure` and `marginal_lineup_value` are exact complements.** Exposure is `measured`
for 100% of rounds 9–15 and unavailable before round 9; marginal value is informative rounds
1–6 and dead by round 10. Together they cover the draft with no gap. Separately, each looked
broken.

**`need_bonus` has zero within-position standard deviation in every round.** It is a
per-position constant. It cannot distinguish two RBs from each other, it moves the board 8.72%
of the value spread on average, and it collapses from round 10.

**They disagree, and exposure is right.** By round 9: `need_bonus` says TE = 0.50 ("you need a
TE") while measured exposure says TE = 4.0 ("your TE is covered"), with RB at 77.9. It is
pointing at the position you are *least* exposed at, because it is a starter-slot heuristic that
structurally cannot see a rostered backup.

**`waiting_cost` is independent of `positional_cliff`** — Spearman **+0.094**. Not a
restatement. 37 rows carry high waiting cost with no cliff signal, and necessity is blind on all
of them.

**Eleven of thirty source-provided fields reach no production reader.**

| field(s) | rows | note |
|---|---|---|
| `std_dev`, `best`, `worst`, `avg`, `analyst_avg` | 552 | expert-panel *disagreement*. Already measured orthogonal in a prior experiment, never wired. The engine has a `confidence` concept with no panel input |
| `bye_week` | 638 | FantasyPros only; real weeks 5–14 |
| `age` | 526 | **a dynasty app that has never read a player's age.** `proj_3yr` is the entire aging proxy |
| `trend_30d` | 499 | KTC market momentum |
| `ecr_1qb`, `ecr_2qb` | 783 | **DO NOT ACT ON — see prohibition below** |
| `injury_flag` | **16** | too sparse to be a signal |

---

## Standing prohibition

`ecr_1qb` / `ecr_2qb` look like an easy fix for the 1QB consensus gap (`_consensus_lookup`
returns empty for 1QB because the KTC export is superflex-only). **They are not.** The
`source_name == "keeptradecut"` filter *is* the CDME ingestion boundary, proven by
`test_cdme_ingestion_boundary.py`'s adversarial injection tests. Recorded here so a later reader
does not helpfully close the gap with it.

---

## What I got wrong today

Three claims were made, then corrected. Recorded because someone reading only the commits
cannot tell which numbers superseded which, and the corrections are more instructive than the
findings.

**1. A broken harness manufactured a defect that did not exist.** The first draft simulation
assigned every pick `roster_id: "x"` — all 56 RBs to one team. `remaining_starter_demand` is
per-team, so the other eleven teams "still needed" RBs forever, freezing the horizon and
producing a fake pool exhaustion. This yielded: `waiting_cost` 39.7% unknown (really **20.0%**),
RB 63.2% unknown (really **26.9%**), and a confident claim that the engine was discarding a
scarcity signal by collapsing "pool exhausts" into "unknown". **The `rank > pool_depth` branch
never fires on real offense data.** Caught by noticing that RB demand held at exactly 29.33 for
fourteen consecutive rounds — a constancy too clean to be real.

**2. `injury_flag` was called usable when it is 16/2600.** I first said prospective injury data
was absent, then "corrected" myself on finding `injury_flag` in `external_values`, then found it
populated on 16 rows. The original statement was right. Prospective injury data really is absent.

**3. The first write-only scanner was too noisy to report.** Scanning all dict literals produced
246 "orphans" that were mostly table headers and label constants, and it misclassified
`waiting_cost` as `DECISION`. Its own non-vacuity check caught that, and it was discarded rather
than reported. The closed-set version (30 known columns) is the one whose result is above.

The pattern in all three: **an instrument that shares its subject's assumptions is not an
instrument.** Already doctrine here; violated three times in one afternoon anyway.

---

## Rulings taken this session

| # | question | ruling |
|---|---|---|
| #71 | name the two costs of waiting | **Player scarcity** (`1 − survival_probability`, wired) and **positional decay** (`waiting_cost`, not wired). Different units, different horizons, independent |
| #87 | is `depth_label` independent of `need_bonus`? | **Unanswerable as posed.** `need_bonus` has no within-position variance, so a correlation test is degenerate by construction. That is very likely why the original measurement was voided. Reframe as between-position, or as ablation |
| — | where does `depth_exposure` feed? | **`team_acquisition_value`** (worth) — owner's call, then hedged and improved: coverage against a hole *is* a roster need, so it bridges both layers. Resolved as a decomposition — see below |
| — | what happens to `need_bonus`? | **Ablate first.** Measure what changes if it is removed before deciding to keep, replace, or repair it |
| — | which orphaned field next? | **`bye_week`** (deterministic; no probability to invent) and **`age`** — but age is *measured against `proj_3yr` first*, since a three-year projection necessarily encodes an aging view and may already price it |

### The bridge, and why it is a decomposition rather than two placements

Exposure alone supports *worth*, not *urgency*. High TE exposure with twelve tight ends still
on the board is an expensive hole you can comfortably wait on. What converts worth into urgency
is the other stranded quantity: `waiting_cost` — how much worse the fallback gets by not acting.

So the two layers read **different functions of the same concern**, never the same number twice:

| layer | reads | claim |
|---|---|---|
| `team_acquisition_value` | `depth_exposure` — the *level* | "this hole is expensive" |
| `pick_necessity` | `waiting_cost` — the *rate* | "and it is getting harder to fill" |

Placing exposure in both would be exactly the double-count this whole pass exists to avoid: the
same position boosted twice for one reason, with nothing downstream able to tell. The
decomposition also lands both stranded quantities — #48's `waiting_cost` and this pass's
`depth_exposure` — in exactly one layer each, which resolves #48 better than wiring
`waiting_cost` into necessity alone would have.

### Hazard on the TAV ruling

`depth_exposure` is only `measured` from round 9, but TAV feeds ordering in all fifteen rounds.
A term that contributes nothing for eight rounds and then switches on is a **discontinuity at
round 9** — the same knife-edge shape as the open complaint in #86. And #58 established that TAV
*saturates*, so a term added there may move less than its arithmetic suggests. Neither changes
the ruling; both constrain the implementation. The basis must gate the contribution explicitly
and the transition must be visible.

---

## Addendum — #139 implemented, and what implementing it turned up

Written after the pass above, on the same branch. The ruling held; three things around it did
not survive contact.

**The term landed as ruled.** `team_acquisition_value = universal_value + need_bonus +
eligibility_bonus + depth_exposure`, converted from `trade_value` into the bpa scale by the
same documented ratio `eligibility_bonus` uses, bounded by `DEPTH_EXPOSURE_MAX = NEED_BONUS_MAX`
— the same number as the other two, deliberately, because they are one class of term and
different magnitudes would rank them by nothing. Contributes only where `depth_basis ==
"measured"`; the other three states contribute `0.0` and that zero means *not measured*, never
*safe*. Upside mode never computes it and emits no column for it.

The predicted round-9 discontinuity is real and visible in the basis rather than hidden: on the
sampled 20-slot shape the board reads `vacant` in rounds 1–5, `no_surplus` mid, and `measured`
from round 6–7 once a bench exists.

**The necessity wiring was built, measured, and reverted.** `roster_fit_component` reads
`need_bonus + eligibility_bonus`, and adding the third term to it looks like an obvious
consistency fix — the bullet's own claim is "this roster's own fit". It was implemented and
measured: up to **7.39** necessity points, **0** argmax flips across 8 real board states. Then
reverted, because the measurement was answering the wrong question. The level/rate
decomposition above is the answer, and a clean measurement does not overturn it. Recorded here
because the next person to notice the asymmetry will reach for the same fix; the exclusion is
now an executable assertion (`DepthExposureStopsAtTheValueLayerTests`) rather than a silence.

**#144 — the same constant borrowed twice, against a quantity that outgrew it.** `NEED_BONUS_MAX`
is the cap on *one* term. Two places compare it against the *sum*:

| site | before #139 | after #139 |
|---|---|---|
| `context_elevated` (`TAV − UV >= NEED_BONUS_MAX`) | max gap **8.33**, fires **0.0%** — recorded as a dead threshold | max **13.21**, fires **7.8%** of 1992 priced rows, all in rounds 6–8 |
| necessity's `denial_component` (`min(rival_premium / NEED_BONUS_MAX, 1)`) | max **8.33**, never bound | max **16.21**, **21.9%** of sampled candidates now clip |

`rival_premium` is `(rival TAV − rival UV)` on the rival's own board, so it picked the term up
automatically — correctly, since a rival's depth hole is as real a reason for them to take a
player as an empty slot is. The divisor did not follow it.

Neither is repaired. The first is a bound that became a discriminator *by accident*, which is
still #56's category error and still an open product decision. The second's structurally
matching divisor is the sum of all three caps, which would divide every denial contribution by
three across every round to fix a tail — a larger change than the problem, against a weight
calibrated on the old range. Both rates are pinned in `test_threshold_reachability.py` so
neither can move unseen.

**One presentation defect, found by generalizing.** The Draft Room's "What changed?" drawer
renders `_DRAFT_ROOM_DIFF_LABELS.get(k, k)` — a missing label shows the raw identifier rather
than failing. Adding `depth_exposure` to the diff fields would have rendered `depth_exposure:
+7.39` to a person; writing the coverage test generally rather than for that one field found
`rival_premium` and `positional_forfeit` had been doing it already. All three now have labels
and the coverage is asserted.

---

## Addendum 2 — #142's two owner-picked fields, and why only one of them got wired

`age` and `bye_week` were the two orphans picked to act on. Both were measured before anything
was built, and the measurements pointed in opposite directions from the obvious plan.

### `age` — the largest unread signal in the input, and adding a term is the wrong fix

Coverage is not the problem: **100% of QB/RB/TE and 98% of WR** in the valuation frame resolve
an age. The gap is IDP (~5%) and DEF (0%) — #51's supply problem, not this one. So the
`roster_diagnostics` note claiming the repository "carries no age or experience field at all"
was true of that harness and false of the repo; corrected in place rather than rewritten away.

The measurement ran in three steps, each correcting the one before:

| step | QB | RB | WR | TE |
|---|---|---|---|---|
| raw `r(age, trade_value)` within position | +0.05 | −0.02 | +0.12 | −0.27 |
| **partial, holding current projection fixed** | **−0.50** | **−0.68** | **−0.52** | **−0.55** |

The raw row is a trap, and taking it at face value would have closed this as "the market
doesn't price age" — which is absurd for a dynasty product. Two confounds cancel the effect
almost exactly: the young cohort is full of unproven depth, and the old cohort is
survivorship-filtered to players good enough to still be rostered at 30. Control for current
production and the discount is enormous. Matched pairs say it without a coefficient:

    D Henry    32  proj 262 -> tv 26      O Hampton   23  proj 254 -> tv 73
    T Kelce    36  proj 221 -> tv  6      H Fannin    22  proj 236 -> tv 56
    D Adams    33  proj 230 -> tv 22      M Nabers    23  proj 237 -> tv 81

**Almost none of it reaches `universal_value`.** `bpa` is VOR in raw projected POINTS — a
current-season quantity with no aging discount in it — so the only channel is
`time_horizon_adj`, clamped to ±10 on a scale spanning ~500. On same-position pairs within 15
projected points where the market prefers the younger player:

| age gap | pairs | engine agrees | mean market ratio |
|---|---|---|---|
| 0–2 | 262 | 68.3% | 6.88× |
| 3–5 | 254 | 58.7% | 8.98× |
| 6–8 | 100 | 65.0% | 7.51× |
| **9+** | 33 | **51.5%** | 4.33× |

The rate *falling* as the gap widens is the signature: where the market is most certain, the
engine is least aligned. A weakly-read signal gives a flat rate; an unread one gives this.

**Not wired, and the reason is the magnitude, not the evidence.** A fourth bounded additive
nudge cannot close a 4–9× pricing gap, and picking a bound big enough to try would invent
exactly the number #56 forbids. What this actually indicts is the dynasty horizon layer's own
size, which is #50's subject and #81's contract. Delivered instead as
`run_age_signal_measurement.py` — a committed, re-runnable instrument that hands #50 its
evidence and can be re-run against whatever #50 produces.

### `bye_week` — derivable at 99.1%, real in deep lineups, and still not a scoring term

The per-player column is non-null on 638/2600 rows and joins to 66.5% of the valuation frame.
But **a bye belongs to an NFL team, not a player**: collapsing to a team map lifts coverage to
**99.1%**. Verified on the baseline — 32 teams, 0 internal conflicts, weeks 5–14. A team whose
rows disagree is dropped and reported rather than resolved by majority vote, because a conflict
there means rows are attached to the wrong players (#77, #78) and picking a winner hides it.

Then the question that decides whether to price it — does the engine actually have this
problem?

    chance baseline, 8 starters   mean worst week 2.62   (46.9% at 2, 41.4% at 3)
    engine's own 12 rosters       median 2, max 3, 5/12 at 3+
    best reachable                the top-value legal eight ALREADY sits at the floor;
                                  no swap within 10 universal_value points improves it

The engine is not clustering byes — it is not avoiding them either, and on this shape those are
the same number. Reachable gain: roughly one starter in one **known** week.

> **CORRECTED — that conclusion was measured on the wrong quantity.** The headcount reading
> above is true and nearly irrelevant. Re-measured in VALUE terms on twelve fully-drafted
> rosters from one league: worst-week losses ran **41 to 127** trade_value while every roster
> sat at the pigeonhole floor for starters-out. The bodies were spread; the value was not.
> Concentration — the share of a roster's total bye damage landing in one week — ranged **0.25
> to 0.62** across the same twelve. Reassigning the *same players* to a staggered profile cut
> roster 3's worst week from **127 to 69**; median reachable gain 9.0, tail 58.0, which is ~7
> bpa against a `NEED_BONUS_MAX` of 12.
>
> The mechanism, and why a headcount cannot see it: spread your byes and every week you field
> starters plus your first-up depth. Stack them and one week consumes two or three bodies at
> once — and bench value decays, so the same absences cost more together than apart.
> `bye_collision` now reports `bench_used` and `bench_value_used` per week, and
> `bye_concentration` reports the shape, both traceable to the week that caused them.
>
> **No depth RANK is reported, and that is a correction, not an omission.** Two definitions
> were built and both were unsound, because FLEX substitution routes coverage across positions:
> a WR going out is covered by sliding the *flexed* WR up into the WR slot and dropping a bench
> **RB** into the vacated FLEX. Verified on a real fixture — that chain costs **5** where the
> naive "best bench WR" reading predicts **16**. A per-position rank then calls the covering RB
> "depth 1 among RBs" when he is not covering an RB hole; a global rank calls him "depth 2"
> whenever a better body went unused, implying waste the optimal solve did not commit. The
> count and the value consumed survive because neither depends on routing, and `value_lost`
> already carries the exact cost with the chain included.
>
> This does not by itself make it a scoring term — that decision is open, and now has evidence
> behind it where before it had a measurement pointing the other way. It does grow with
lineup depth (simulated against the real 32-team spread: 12 starters → mean 3.49; 20-starter
IDP → 5.12, where the pigeonhole floor is itself 3), so the function is built to be read at any
shape — but a term that cannot improve the outcome it targets is #138's defect with the arrow
reversed.

**Built as `lineup_optimizer.bye_collision`, read by `roster_diagnostics.TeamDiagnostics`, and
scored by nothing.** It measures VALUE lost, not bodies lost — a roster covering three absences
from its bench loses nothing, and a headcount ranks it below one losing a single irreplaceable
starter. It is also the genuine extension of `depth_exposure` rather than a loop over it:
removing several starters *simultaneously* is superadditive, because the bench covers the first
hole and has nothing left for the second. `test_bye_collision` asserts both the mechanism and
the refusal, so wiring it later means deleting a test that explains why not.

---

## State at the end of this pass

- `main` merged and unfrozen at `cf8fa0c`; marker branch `pre-blind-audit` sits there.
- Branch `ui-authority-pass` at `8638159`. Full suite **1,968 tests**.
- The `pre-hull-extraction` freeze is deliberately **not** placed. It marks the moment before
  the hull moves, and the hull is not moving until the brain is finished — placing it now would
  put engine work between the marker and the extraction, mixing both into one diff and defeating
  the before/after it exists to provide.
- Agreed sequence: **finish the brain → freeze → audit → fix → merge → freeze v2 → extract.**
