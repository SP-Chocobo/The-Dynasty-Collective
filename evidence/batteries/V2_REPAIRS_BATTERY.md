# The battery over the v2 repairs — COMPLETE, 53 arms, 9336 picks

**Status: complete. `complete: true`, 53 of 53 arms, 53 independent (no duplicates), 21 structural
findings, 2920.2s of drafting.**

## Provenance, stated because the run spans two commits

51 arms were drafted at **`360f6ba`** — the handoff immediately after 2.6 was certified — and are
carried forward. The container was recycled at 51 arms and the run resumed, so the last 2 arms were
drafted at **`6ea4f5b`**, with every repair in. Each arm records its own `produced_at_commit` and
`carried_forward`, so nothing here is a mixed-code average.

    commits_present: ['360f6ba', '6ea4f5b']
    carried_forward: 51 True, 2 False

## The findings: 21, and every one is 3.2's fieldability ceiling

| arm | findings | audit |
|---|---|---|
| `HEAVY_IDP` | 10 | `unfieldable_depth` |
| `HEAVY_IDP_balanced_full` | 11 | `unfieldable_depth` |
| **the other 51 arms** | **0** | — |

Every offence-only arm returned zero. The single structural class the battery can find is the one
3.2 names, and it is confined to the two arms that field dedicated IDP slots.

**Both were re-drafted against the repair and both collapse:** `HEAVY_IDP` **10 → 1**,
`HEAVY_IDP_balanced_full` **11 → 1**. So **21 → 2**, and both survivors are genuine group overflows
reported per group, not the per-position counting defect. See
`evidence/fieldability_joint_bound/`.

## What else the report says, swept for anything the `findings` field would miss

- **No unpriced candidate ever won a decision**, across all 9336 picks. That is the admission
  contract (`#193`) and the absence contract (`#187`) holding on real drafts rather than in a test.
- **All 53 arms report a `contested` decision regime** — none collapsed into a degenerate one.
- **No duplicate arms**: 53 labels, 53 independent formats.
- All three replacement bases appear across arms (`live_starter_demand`, `predraft_anchor`,
  `startable_floor`); no arm priced off a single basis.
- The two arms drafted fresh on repaired code — `CAPTURE_fourth_and_forever_balanced_full` (312
  picks) and `12T_ppr_K_DEF_balanced_full` (192 picks) — both returned **0 findings**. The second
  matters on its own: it is the arm that fields a K and a DEF slot, so it exercises 2.3's kicker
  repricing and `#30`'s streaming floor, and it is clean.

## The upside growth term, measured at 100× the population the mandate had

The report carries `picks_with_growth_measured` and `picks_with_growth_above_zero` per arm. Summed:

| | |
|---|---|
| picks where growth was measured at all | **672** of 9336 |
| picks where growth was **above zero** | **5** |
| share of measured picks | **0.74%** |
| arms with any pick above zero | **3 of 53** |
| `max_growth` across arms | 0.0 to 19.8 |

The mandate's own figure is "positive on 2 of 87 real picks", and it flags that number as **mine**,
from the pre-freeze `evidence/upside_gap/` work, with an independence problem — my commit subject
leaked it into a `git log` that pass A could read. **This measurement is independent of that**: it is
the battery's own instrument, over 53 arms and 9336 picks, and it agrees. The term is inert at scale.

That changes what D4 is asking. At 5 of 672 the live question is not what conversion the term should
use — it is whether a term that fires on 0.74% of the picks that reach it should exist at all.

## No repair follows from this run

Every finding is accounted for by 3.2, which is repaired and verified twice. Nothing else in the
report flags a defect. The remaining items are owner decisions, not repairs.
