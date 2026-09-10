# Step 1 — the intended semantic purpose of upside mode, traced from source

Brief step 1. **Reads only; no engine source changed.** Every quotation below is verbatim from
the working tree at `fe03939`. Steps 2 and 3 (the candidate enumeration) are NOT done yet; step
4 is partially done (tests found and read). The deliverable question is not answered here.

---

## 1. What the engine says upside mode is FOR — three sources, and they agree

**Module docstring, `draft_room.py`:**

> UPSIDE MODE (round >= UPSIDE_MODE_DEFAULT_ROUND, or toggled on explicitly): **late-round picks
> rarely move a roster's outcome — the real value is finding a league-winner, not optimizing
> safe positional value.** Scores on growth trajectory […] with confidence surfaced separately,
> never folded into the score itself.

**The constant's own comment:**

> Round at which the engine switches from the balanced formula to upside-only scoring, absent an
> explicit override — **matches the "War Room" idea this was modeled on. A deep bench/waiver-fringe
> pick is about finding a league-winning outlier, not filling a need or respecting positional
> scarcity that barely matters by then.**

**`upside_score`'s docstring:** growth trajectory (`proj_3yr` exceeding this season) is the value
driver; cross-source disagreement is surfaced as confidence and never added to the score.

### The intended trigger state, in the engine's own words

> **"a deep bench / waiver-fringe pick"**

with two supporting claims attached: such a pick (a) *"rarely moves a roster's outcome"*, and
(b) sits where *"positional scarcity barely matters by then"*.

That is a **roster-depth** concept. It is a statement about **where this pick lands on the
roster** — past the starters, past the useful bench, into the fringe.

## 2. What the switch actually keys on

```python
current_round = (max((p.get("round") or 1) for p in demand_source) if demand_source else 1)
use_upside   = mode == "upside" or (mode == "auto" and current_round >= upside_round)
```

Three properties, all read from source:

- **GLOBAL, not per-seat.** `max(round)` over every pick in the draft. Every seat flips at the
  same instant regardless of what its own roster looks like.
- **A CALENDAR INDEX, not a depth.** It counts rounds elapsed, not bodies placed.
- **Read off the pick record's `round` field**, with `or 1` — the behavioural-schema hazard
  already in the doctrine.

## 3. The provenance of 15 is documented, and it is EXTERNAL

*"matches the 'War Room' idea this was modeled on."* So the number is not arbitrary — it is
**borrowed from a product reference**, not derived from anything this engine computes.

The repo already classifies it that way itself.
`test_auto_mode_switches_to_upside_exactly_at_the_documented_round`:

> **The boundary itself is a calibration decision** (see UPSIDE_MODE_DEFAULT_ROUND's own
> comment). What must not happen is it moving without anyone noticing […] The literal is
> deliberate — change it here, on purpose, or not at all.

**The test pins the NUMBER and explicitly declines to pin a MEANING.** It is a
change-detector, not a contract. Nothing in it says what state round 15 stands for.

## 4. The gap, stated precisely

The purpose names a **roster-depth** state. The implementation uses a **global calendar index**.
Those coincide only if round N is the same depth in every league. It is not:

| league | starters | bench | rounds | what round 15 IS |
|---|---|---|---|---|
| Fourth and Forever | 10 | 11 (+3 IR, +5 taxi) | 26 | the seat's **5th bench body** |
| the repo's own test league | 7 | 13 | 20 | the seat's **8th bench body** |
| most `draft_battery` formats | — | — | **14** | **never reached** |

So the constant does not express the concept its own comment names. It buys a different roster
depth in every format, and in a 14-round format it buys nothing at all.

## 5. The fact that reframes the question — nothing human ever reaches it

Verified directly in this session, not inherited from the audit:

- `pick_synthesis.build_snapshot`'s signature default is **`mode: str = "balanced"`**.
- `app.py` has **three** `build_snapshot` call sites (lines 4959, 5014, 5365). **None passes
  `mode=`.** They pass `pick_label`, `pool_scope`, and on the Draft Room path the Sleeper
  projections — nothing else.
- `app.py` makes **zero** direct `compute_draft_board` calls, so `compute_draft_board`'s own
  `mode="auto"` default is never the governing one in the product.

**Therefore a human's board is always balanced and never enters upside mode** — no automatic
switch, and the explicit toggle that `compute_draft_board`'s docstring refers to ("the toggle
this was built for — see app.py's Draft Room view") is not wired at any of the three call sites.

This is already recorded — `ARCHITECTURE_AUDIT.md` §20.6 and register item **#115** — and
`draft_battery.py`'s own comment states the consequence plainly:

> most formats here are 14 rounds, so **auto never reached upside at all**. The battery would
> have reported "modes covered" while exercising one. Measured on the smoke run before this was
> fixed: 0 picks with a growth_signal across 280 picks in two formats. […] #115 records that a
> human board never reaches it — **which makes the simulation the ONLY place its behaviour is
> observable at all.**

So the 46%-of-the-draft roster-blind window #222 measured is a **simulation-only regime**. It is
reached by `simulate_full_draft` (`mode="auto"`), by auto-drafted opponents, and by the two
battery arms that force the mode explicitly. It is not reached by the product.

**What this does NOT mean.** It does not make #216 irrelevant: the battery certifies the engine,
every simulated opponent drafts through this path, and the roster shape #222 measured is real.
It does mean the defect class is different from "the human's late-round advice is wrong" —
nobody has ever received that advice.

## 6. Where this leaves the deliverable question

Not answered yet — steps 2 and 3 are outstanding, and the enumeration is explicitly not closed.
What step 1 establishes is the **target the enumeration must be measured against**:

> Does the architecture contain a quantity meaning **"this pick is a deep bench / waiver-fringe
> pick for THIS seat"**?

Note what that phrasing rules in and out. It is **per-seat** (the current switch is global), and
it is **roster-depth relative** (the current switch is a calendar index). Any candidate that
answers a *league-market* question — "has league-wide starter demand run out?" — is answering a
different question from the one the engine's own comments ask, however defensible it may be on
its own terms.

One candidate is already visible and was NOT in the previous session's five:
**`lineup_optimizer.bench_capacity`** — it counts this league's `BN` slots directly from
`roster_positions`, which is the denominator "deep bench" needs. Register item **#115** records
that it *is not an engine input*. Whether it, combined with a seat's own pick count, expresses
the stated concept is a step-2/3 question and is not decided here.

## What I did not do

- Did not tune, wire, or propose a transition rule.
- Did not run any probe or ablation — this step is entirely reads.
- Did not complete the step-2 enumeration or the step-3 per-candidate analysis.
- Did not touch the residual TE / B2 questions.
