# The register lagged the repairs, and "has a dedicated test" is not a closure signal

Found by nearly redoing closed work. Picking #187 (`denial_value` emits an unmeasured 0.0 while
the tooltip promises it was measured) off the open list, the first grep found the repair already
shipped: the derived vocabulary `DENIAL_MEASURED` / `DENIAL_NO_INTERVENING_RIVAL` /
`DENIAL_NO_RIVAL_PRICED` in `draft_strategy.py`, `denial_value = None` where nothing was
measured, and a `test_denial_basis.py` that additionally forbids reconstructing the basis from
`denial_value == 0`. Same for #190 and #207. All three ran green. All three were still filed
open.

**The cost of this is re-derivation, and it is silent.** Nothing fails. The item reads open, the
investigation starts, and the only thing that stops it is a grep landing on the repair. That is
luck, not a process.

## What was swept

Every item still filed open was screened for a test naming it — 52 items, against every
`test_*.py` in the tree. **30 of 52 have at least one.** That is the screen, not the verdict.

## Why the screen cannot be a verdict, with a counterexample made this session

A test naming an item means somebody wrote code about it. It does **not** mean the item closed.
The counterexample is one I created an hour earlier: `TheTrendSignSurvivesTheParserTests` names
#148 and is green, and **#148 is open and stays open** — the test is a *guard on an open
condition*, pinning that the export is still all-non-negative so the day a signed capture lands,
it fails and the record gets retired. #209 and #210 look like the same shape: supply gaps whose
tests guard a still-missing input.

So the two populations are not separable by grep. A green test naming an item means either
"repaired and pinned" or "open and guarded", and only the item's own verdict distinguishes them.

## What was verified and flipped

Six items, each confirmed three ways — repair visible in source, dedicated test green, and a
verdict in the register or the task's own title:

| item | what shipped | pinned by |
|---|---|---|
| #185 | superflex QB rows say `startable_floor`, not a false `live_starter_demand` | `test_replacement_basis_vocabulary` |
| #187 | `denial_value` is `None` where unmeasured; basis vocabulary derived | `test_denial_basis` |
| #190 | `positional_depth` raises `count` for all, `value` only for the priced | `test_positional_depth_coverage` |
| #192 | the scoring-aware path has a production caller at every position | `test_battery_pricing_path` |
| #193 | admission and pricing separated; vendor coverage is not the universe | `test_battery_universe_boundary` |
| #207 | `rival_premium` carries a basis — the sibling in the same loop | `test_absence_survives_consumers` |

#185 is confirmed at `735c972` in the register itself; #192 is independently confirmed by #180
closing as ALREADY REPAIRED *by* #192's work. 120 tests green across the verification runs.

## What was NOT flipped, and why

**#208, #209, #210, #211** each have a green dedicated test and **no recorded verdict anywhere in
the register** — their status lives only in task titles and evidence files. Two of them (#209,
#210) are supply gaps, the shape most likely to be open-with-a-guard. These need adjudication
against their own evidence, not a status flip on a grep. They are named here so the next pass
starts from the list rather than rediscovering it.

The remaining 22 screened items have no test naming them at all, which is weak evidence of open
and no evidence of anything else.

## The structural point

This is #126's rule ("one home for a vocabulary; derive, never hand-list") applied to the
register itself. Completion state currently lives in three places that can disagree — the task
list's status field, the task's own title prose, and POST_AUDIT_PLAN's verdict sections — and
for the items numbered above ~205 the register section was simply never written, so the title
prose became the only record. Three sources of truth for one fact is the defect this repo
otherwise refuses everywhere.

**The narrow lesson, worth more than the bookkeeping:** before opening an investigation into any
item filed open, grep for its repair first. It costs one command and it would have saved this
session an entire investigation.
