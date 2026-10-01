# Phase 1.2 — the remaining identity class, measured, repaired, and frozen

> Measured against the **post-Phase-1.1** population (775 priced rows), not against v1.

## Invariants established

| # | invariant | before | after |
|---|---|---|---|
| 1 | A player's rookie status cannot be inherited from a namesake | 788 pool players hit the lookup, **58 wrong** | **22 wrong**, all same-namespace; the rest refused rather than guessed. **Residual left open by ruling** |
| 2 | A normalized name that names two position groups is ranked in **neither** pool | 19 cross-group keys silently collapsed to the first row's group | 19 keys answer `None`; ranked in neither |
| 3 | A textual match is not an identity | **7 cross-namespace resolutions** returned `matched` and `verified=True` | **0** |

## What each repair was, and what it deliberately was not

**1. Rookie (`_rookie_lookup`).** Keyed on `(name_key, identity_namespace)` — the merger's own
namespace, exposed as a public `identity_namespace()` rather than importing the private
`_position_group`, so the two position keys in this codebase keep one home each. A key whose rows
still **disagree** is dropped, not resolved by row order.

**The residual 22 are honest and structural, and they stay open.** Jonathan Taylor and Jmari
Taylor are both RB; Jordan Love and Jeremiyah Love are both offense. No namespace separates them,
so the repair **refuses** them rather than guessing, and refusal falls through to this function's
documented rule for a player KTC does not cover.

**Registered as an explicit open identity issue, not a closed one.** Closing it requires per-player
identity, which is the design question below. Until that is ruled, 22 pool players have no correct
rookie answer available and the engine says so by declining rather than by inventing one.

> **OPEN DESIGN QUESTION — explicitly carried forward, NOT resolved here.** There are two
> definitions of "rookie" in this engine, and the owner has ruled that the choice between them is
> **not** to be settled inside an identity repair.
>
> The distinction that decides it: *"can this field identify the player without collisions?"* and
> *"does this field define rookie eligibility correctly?"* are two different questions.
> `years_exp` answers the first — it is per-player-id and cannot be inherited by a namesake. It
> does **not** thereby answer the second for every league and use case.
>
> **Measured consequence of promoting `years_exp`, recorded so the decision can be made on
> numbers rather than on which primitive is tidier: 654 players enter the rookie pool and 31
> leave. A rookie draft goes from 95 players to 718.**
>
> That population change is **not implemented**. It was implemented once, briefly, and reverted:
> a sevenfold change in what a rookie draft contains is precisely the semantic blast radius that
> needs its own ruling, and bundling it into a collision fix is the boundary violation this audit
> exists to catch. I conflated the two questions the moment the cleaner primitive was in front of
> me; the revert is on the record rather than the history being tidied.

**2. Percentiles (`_compute_percentiles`).** `setdefault` → first-row-wins became a set of groups
per key, resolving to `None` when a key names more than one. A key that names two groups does not
name a pool; ranking an offensive player against defenders by coin flip is the error the
segmentation exists to prevent.

**3. `_resolve` (exact and alias paths).** Both narrowed by team and position **only when more than
one row survived**, so a single row of the wrong namespace was returned — as `verified=True`, the
strongest claim the function makes. Both now apply the same namespace rejection the key path
already applied. Deliberately **not** the team rejection: the key path's comment explains that a
team mismatch on an exact full-name match is more likely stale roster data than a different person,
and that reasoning is sound and untouched. It does not carry over to namespace.

## The fifth refuted null

Two Wave 6 passes enumerated `_resolve`'s branches, correctly identified the exact and alias paths
as unguarded, measured **0 crossings**, and filed a null — one of them explicitly "not confident".
The crossings appear only when the query names a position **no row of that name holds**, which is
what a roster-side lookup produces. Measured here: **7**.

That is the fifth pass null refuted in this audit. The rule stands: a null is where a pass looked.

## Mutation evidence — because a green suite is not proof

Each repair was reverted in a tree copy and the new tests re-run:

```
dedup key back to bare norm_name              CAUGHT   (3 failures)
rookie lookup back to bare name key           CAUGHT   (3 failures)
_resolve exact: drop the namespace rejection  CAUGHT   (1 failure)
```

**The first run of this battery caught me, not the code.** The rookie mutation **SURVIVED**: my
test asserted `len(key) == 2`, and a bare `("j", "love")` name key is also a 2-tuple, while two
sibling tests used `if key in lookup`, which goes silent exactly when the key shape changes. I had
written the defect class I was repairing — an invariant pinned where it cannot fail. The tests now
assert what the key's components *are*, and use `assertIn` rather than a conditional.

A second self-correction is recorded in the tests themselves: a draft of
`test_neither_love_inherits_the_others_flag` asserted Jordan Love **had** an entry, which
contradicts the repair's own refusal contract. The test was wrong, not the code.

## One pre-existing defect newly exposed, marked and not repaired

`test_eligibility_bonus_cannot_flip_a_large_universal_value_gap` now fails, and the test is the
correct party:

```
LEADER    P Nacua   uv=155.13  need=0.67  elig=0.00  displacement_adj=-92.0  final=63.80
CANDIDATE D London  uv= 76.20  need=0.67  elig=8.88  displacement_adj=  0.0  final=85.75
```

A 78.93-point universal_value gap is inverted by a **92-point displacement hit on the leader** —
not by the context terms the test bounds. `displacement_adj` is the fourth team term, excluded from
`TEAM_SPECIFIC_CAPS` on the stated premise that it "is non-positive by construction … so it cannot
raise the sum these caps bound". That premise bounds only how far TAV can rise **above** UV.
Nothing bounds how far it **falls below**.

Marked `@unittest.expectedFailure` with the decomposition in place, because this belongs to the
invariant phase and a fix landed here would be measured against a pool that Phases 2–3 are about to
change again. Editing the assertion to pass is the exact move this audit exists to catch.

## Frozen — as an identity repair, not as a semantic resolution

**Phase 1.2 is closed as an IDENTITY repair. It is not a final resolution of what "rookie" means.**
That distinction is the whole adjudication:

- the `58 → 22` reduction is **accepted** as the identity fix;
- the 22 residual same-namespace collisions are **accepted as unresolved** — refused rather than
  guessed, and carried as an open identity issue;
- the `7 → 0` `_resolve` repair is **accepted**;
- the newly exposed W4-02 displacement inversion stays **marked and deferred** to the invariant
  phase, repaired nowhere near here;
- the rookie *population definition* is **carried forward as an explicit open design decision**.

**Two further owner rulings, recorded so they are not re-litigated:**

- **Advance to Phase 2 (provenance)** — the league-upload override boundary and declared-date
  validation, with the rookie-definition question carried forward rather than silently resolved by
  implementation.
- **Absence does not compete on recency.** `_recency_weight` prices an undated source as exactly
  60 days old, so an honestly-dated 89-day-old file loses to an undated upload. Ruled: **a dated
  source always outranks an undated one**, whatever its age, consistent with this codebase's
  contract that "unmeasured" is not a value and must not be assigned one.
