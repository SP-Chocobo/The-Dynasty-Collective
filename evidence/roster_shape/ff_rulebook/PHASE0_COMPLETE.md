# Phase 0 -- the instrument, made trustworthy

**Status: work items 0.1-0.3 complete. The phase GATE is partially evidenced with the
reproduction deferred -- see the Gate section. Do not read this file as "Phase 0 is
done" without that qualifier.**

PLAN_222 Phase 0. **No engine source changed.** `draft_room.py`, `lineup_optimizer.py` and
`pick_synthesis.py` are byte-identical to where #222 started. What changed is the harness
that measures them, and the written recipe that tells the next probe how.

The order matters and is the standing one: *evidence before repair, repair before freeze.*
This is not repair. It is the thing that makes the next repair believable, and it exists
because two published findings in this investigation were withdrawn for instrument defects
rather than reasoning defects.

---

## 0.1 -- the recipe (B5, closed)

`.claude/skills/engine-measurement/SKILL.md` named `rdb.build_players_db` in its opening
fixture: the 764-row vendor reconstruction that #201 superseded. A probe following the
documented recipe measured the wrong population and got plausible numbers about it, which is
exactly what happened to FINDING_01 through FINDING_04 of this investigation.

The fixture now reads:

```python
merger = dm.DataMerger()                                    # 1. from the REPO ROOT
players_db, prov = rdb.build_players_db_from_capture()      # 2. the REAL universe, 6,595
season = rdb.season_projections_from_capture()              # 3. price the way production does
merger.set_league_format(db.league_format_hint(league))     # 4. NEVER SKIP THIS
```

with `sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM` into
`build_snapshot`, and a one-line cross-check for any probe that builds a board and a draft
separately:

```python
assert set(board["player_id"]) >= {p.chosen_player_id for p in traj.picks}
```

That assertion is the whole of what would have caught the wrong-universe error on the day it
was made instead of four findings later.

## 0.2 -- the guard (new)

`run_draft_battery.build_players_db` now RAISES while `data/fixtures/sleeper_capture.json`
exists, unless the caller passes `recorded_universe=True`.

The flag is deliberately not a boolean anyone can set to make an error go away: it means *"I
am one of the recorded measurements whose published results are stated against this pool"*,
and exactly one caller qualifies -- `run_demand_reach_audit.py`, whose numbers are on record
against the reconstruction. #201 kept that builder alive for precisely this reason, and
deleting it would make a recorded experiment describe a different universe under the same
name.

Why a runtime raise rather than another static scan: #201's protection was at the BATTERY's
entry point, and `test_battery_universe_boundary` pins `main()` statically. Neither reaches a
hand-written probe, and a hand-written probe is what went wrong. The two id spaces overlap on
373 ids **coincidentally**, so the wrong universe never crashes and never looks empty. The
guard has to be at the call.

Four tests, each mutation-checked -- guard fires; recorded consumer still works; no capture
present means nothing to prefer; the recorded consumer declares itself statically. The
inverted-condition mutation also took down a fifth, pre-existing test I had not predicted,
which is the right answer: the other legitimate caller of the reconstruction is the
non-vacuity test for the reconstruction itself, so it moves with the flag by construction.

## 0.3 -- rank is not pick order (B4, registered)

The skill carried this as a parenthesis inside a bullet. It is now a named section, because
three distinct ordinals were being written with one word:

| what it is | what to call it |
|---|---|
| position in the board frame, full pool | `rank_on_board(full pool)` |
| position among players still available | `rank_among_remaining` |
| when the player actually went | `pick_number` |

Phase 2 of this investigation reported "rank 37 of 198 REMAINING receivers" and had to
withdraw the word *remaining*: the captured call was the pre-draft anchor over the full pool.
One word, two meanings, one withdrawn finding.

## The doctrine, promoted

Both clauses earned in this investigation are now in the skill as a section of their own,
ahead of the runtime budgets, with the withdrawal that produced each one attached:

1. **If the system already computes the quantity under test, OBSERVE that production
   quantity. Never reconstruct it from downstream artifacts.** Three probes recomputed the
   tight-end replacement level from `compute_draft_board`'s output rows. That is a second
   implementation, and a second implementation is a second source of truth (#126). It agreed
   with production at some board states and not others -- which is why B1 read as a defect and
   survived three rounds of checking before being withdrawn.

2. **When a function is called more than once per operation, the instrument must identify
   WHICH CALL it captured.** `replacement_levels` runs at least three times per board build
   (pre-draft anchor over the full pool; live on `_points`; live on `trade_value`). Derive the
   tag from the ARGUMENTS, never from call order -- a cache can change order silently, and a
   spy that sees two calls where you expected three has told you something rather than failed.

The skill's preamble now says the quiet part: #150's errors were all FIXTURE errors, and #222
added a second family with the same shape and a different cause -- the fixture was right and
the INSTRUMENT was wrong.

---

## Gate

PLAN_222's gate for this phase is *"the skill's recipe reproduces FINDING_05's draft exactly."*

**GATE PARTIALLY EVIDENCED / REPRODUCTION DEFERRED** -- because the exact artifact already
exists and the recipe is byte-equivalent to the producing recipe.

That is the whole claim, and it is deliberately weaker than the gate. The gate says the
corrected recipe must REPRODUCE the draft. What is established is that the recipe now written
in the skill is character-for-character the one `run_ff_draft.py` used to produce
FINDING_05, and that the draft is determinism-checked (the 3RR arm reproduced identical
totals from a different pick order; a rerun of the same arm was byte-identical).

**"We know this recipe produced the artifact" is not "we freshly demonstrated that it
reproduces the artifact."** The second is what the gate asks for and it has not been done. The
~1,125-second re-run was not spent, because it would have been ceremony against a number
already saved in `ff_draft.json`.

This gap stays OPEN and visible until the first change to the pricing path, at which point the
re-run stops being redundant and becomes mandatory. It is not closed by this document.

## What this phase deliberately did NOT do

- **No engine change.** The #50 anchor ruling is still the owner's, and
  `RULING_INPUT_50_anchor_semantics.md` is still the input to it.
- **No move on the flex-anchor candidate.** It stays stranded, for the three reasons already
  recorded -- the newest being that it was derived on the assumption that replacement
  behaviour was malformed, and that assumption is now dead.
- **No re-run of the battery.** Phase 4, after a ruling.
