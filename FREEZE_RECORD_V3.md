# v3 FREEZE RECORD — what it rests on, what it does NOT claim, and what was left open

> **v3 IS NOT PRODUCTION, AND THAT IS THE POINT OF IT.** v3 claims one thing: *every known finding
> is repaired and all seven owner decisions are resolved.* That is a claim about the COMPLETENESS OF
> KNOWN WORK. It is not a claim about correctness under an adversary, which is what `v4-freeze` is
> for and what the three-instrument gate in `ROADMAP_TO_FREEZE.md` exists to establish.
>
> The owner set the rule this record follows: *make the version numbers correspond to evidence, not
> calendar time.* So each claim below names its evidence, and the claims this freeze does not make
> are listed as plainly as the ones it does.
>
> `POST_AUDIT_PLAN.md` remains the numbered record and wins over any status flag anywhere (`#292`).
> Written to be read cold.

## PUBLISHED AND VERIFIED

`v3-freeze` was pushed by the owner on 2026-09-30. The tag object is
`1f3affa44a04350e31460c10f585a3f65bb9e5a7` and it dereferences to
`eac74913a4cf29b6aae681b251649747b6b0d2c5` — this record's own commit — confirmed against the
remote rather than assumed. Recorded here because v2's record could not answer the same question
later without a `git tag -l`, which is the omission that produced the v2/v3 numbering error.

The tag was cut in the cloud container and could not be pushed from there, so the owner created it
locally at the same commit and pushed it. The published tag object is therefore theirs, not the one
cut here; both point at `eac7491`, and the published one is the authority.

## The chronology, because a version number means nothing without it

| | |
|---|---|
| `v1-freeze` | `6599b1e` |
| a premature v2 tag at `43c8188` | cut, then **deleted** — the varied-field battery had not run |
| **`v2-freeze` at `a8d1627`** | cut for real and published, full suite 3512 OK |
| `#52` — the Fable blind adversarial pass | unbriefed, after the freeze; nine pass reports recorded verbatim |
| `REPAIR_MANDATE_V2.md`, 26 items in five tiers | every tier certified |
| the 53-arm battery | 9336 picks, complete, and **no repair followed from it** |
| the seven owner decisions | answered in a picker, then shipped over phases A1–A3 |
| **`v3-freeze`** | this record |

**A correction belongs in this record rather than only in a commit.** While writing the roadmap I
said the upcoming tag was v2, on the strength of a task summary reading *"freeze NOT cut; premature
tag deleted; v2 is a CANDIDATE pending the battery."* That summary described a superseded moment.
The owner caught it, and `#292` is the rule I broke: the record wins over any status flag. The
correction was one `git tag -l` away and I did not look.

## What v3 rests on

**The four mandate tiers, all certified.** Tier 0's instruments (which police my own work), Tier 1's
production defects, Tier 2's outside inputs, Tier 3's engine-internal items, Tier 4's
one-concept-two-homes consolidations.

**A clean battery.** 53 arms, 9336 picks, 21 structural findings — all 21 `unfieldable_depth` on the
two dedicated-IDP arms, both re-drafted against 3.2's repair and collapsing 10 → 1 and 11 → 1. A
sweep past the findings field confirmed no unpriced candidate ever won a decision across 9336 picks,
all 53 arms were in a contested regime, and no arms duplicated.

**All seven owner decisions, shipped and measured.** D1 pinned, D2 closed on both surfaces, D4
re-derived, D5 stated as a convention, D6 discharged into D9, D7 shipped multiplicatively, D8
re-derived proportionally.

**Full suite green at every push:** 4041, 4065, 4076, and again at this freeze commit.

**D7 verified on real drafts, not only on stored rosters.** The factor was chosen on a static sweep;
a sort key only matters if it reaches a pick, so a seven-arm battery re-drafted every league where
the new bound can bind plus the deepest offence rosters in the population — 1824 picks, all at
`7070339`. `LIGHT_IDP` went from six seats over the bound to **none**, capped at exactly 4, which is
D7's ceiling for that league and a number nothing else computes. All four `CAPTURE` arms returned
zero findings. The two `HEAVY_IDP` findings are the already-certified DEDICATED bound's known
survivors. Recorded in `evidence/d7_flex_depth/`, including the caveat that the before/after spans
A1–A3 and is therefore not single-variable.

## What v3 does NOT claim

**It does not claim the engine is correct.** It claims the known findings are repaired. The
difference is the whole reason v4 exists, and the reason `ROADMAP_TO_FREEZE.md` defines a gate with
three instruments rather than re-running the one that is cheapest.

**It does not claim the battery is an adversarial instrument.** It is a REGRESSION instrument:
deterministic given code and data, fixed assertions over fixed fixtures. Re-running it proves
nothing known broke. That is necessary and it is not a gate.

**It does not claim independence.** Every one of the commits since `a8d1627` is mine, and the only
things that have read them are my own instruments. The v2 blind pass found that all three invariant
mutations SURVIVED the engine suite while two committed verdicts claimed otherwise (`dbc4d4a`) — a
self-certification instrument reporting false positives about its own detection power. That is the
standing reason to distrust "the suite is green" as an independence claim.

**It does not claim the constants are right.** Three numbers in this engine are conventions, stated
as such: `FLEX_GROUP_DEPTH_FACTOR` (3.0, inside a measured window), `Doubtful`'s assumed half-game,
and 1.3's tie-break. `#56` forbids calibrating a constant, and each of these is recorded as chosen
rather than derived.

## What was left open, deliberately

Each has its reasoning written down in `OWNER_DECISIONS_PENDING.md`. None is a silent debt; none is
a defect.

* **D9 / `#50`** — the replacement equation. The owner's call, now written up with both of its own
  premises corrected: the pre-draft anchor never reaches QB, and the `bpa == 0.00` rows are 5–9 with
  a majority under live demand rather than the anchor. **Blocks `#21` and D7(a).**
* **D1(b)** — `rival_premium`'s own four-state basis vocabulary. Safe to defer because the borrow is
  pinned: the day it stops being true, a test fails loudly.
* **D2(c)** — per-term config refusal. The eventual shape; Tier 3-sized.
* **D4(b)** — a conversion derived from first principles rather than borrowed from
  `TIME_HORIZON_SLOPE`.
* **D7(a)** — the depth factor derived from `#30`'s streaming baseline. Blocked behind D9.
* **D8(a)** — re-deriving `NEED_BONUS_MAX`, `DEPTH_EXPOSURE_MAX` and `TIME_HORIZON_CLAMP`. Needs a
  decision about which spread, which wants a measurement campaign.
* **The 16 board inversions** — cross-position pairs in the opening top 60 where team terms outvote
  the value anchor. Pinned as a watched figure; team-specific terms are supposed to be able to
  reorder a board.

## The stopping rule this freeze establishes

After `v4-freeze`, the engine and its test layers change for two reasons only: **new or changed
inputs**, and **a catastrophic defect** (the board prices something it cannot justify, or a number
reaches a person with a basis that is false). Anything else is RECORDED, not repaired.

Between v3 and v4 the scope is narrower still: the gate's pass/fail criteria are written BEFORE the
gate runs, including what is out of scope, and a finding outside that scope is recorded rather than
repaired. Without that clause, v4 becomes v5 by exactly the mechanism that produced v3.
